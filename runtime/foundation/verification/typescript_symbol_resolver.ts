#!/usr/bin/env npx tsx
import { Project, SyntaxKind, Node } from "ts-morph";
import { existsSync, statSync, writeFileSync, mkdirSync, readFileSync } from "fs";
import { join, resolve, relative, extname } from "path";

interface SymbolInfo { name: string; kind: string; file: string; startLine: number; endLine: number; exported: boolean; isReactComponent: boolean; isHook: boolean; }
interface CacheData { [k: string]: { mtime: number; symbols: SymbolInfo[] }; }

async function main() {
  const args = process.argv.slice(2);
  if (!args.length) { console.error("Usage: <file_or_dir>"); process.exit(1); }
  // When run from frontend/, repoRoot is parent; when run from repo root, repoRoot is cwd
  const cwd = process.cwd();
  const possibleFrontendRoot = cwd.endsWith('/frontend') ? cwd : join(cwd, 'frontend');
  const repoRoot = possibleFrontendRoot.endsWith('/frontend') ? resolve(possibleFrontendRoot, '..') : cwd;
  const inputPath = resolve(repoRoot, args[0]);
  const cacheDir = "runtime/generated/typescript-symbol-cache";
  const cacheFile = join(repoRoot, cacheDir, "symbol-cache.json");
  mkdirSync(join(repoRoot, cacheDir), {recursive:true});
  let cache: CacheData = {};
  if (existsSync(cacheFile)) { try { cache = JSON.parse(require("fs").readFileSync(cacheFile,"utf-8")); } catch {} }
  const project = new Project({ tsConfigFilePath: join(repoRoot, "frontend/tsconfig.json"), skipAddingFilesFromTsConfig: true });
  const files: string[] = [];
  function walk(dir: string) { for (const e of require("fs").readdirSync(dir,{withFileTypes:true})) { const p=join(dir,e.name); if(e.isDirectory()&&!["node_modules",".next","dist"].includes(e.name))walk(p); else if(e.isFile()&&(extname(e.name)===".ts"||extname(e.name)===".tsx"))files.push(p); } }
  walk(inputPath);
  const results = [];
  for (const fp of files) {
    const rp = relative(repoRoot, fp);
    const s = statSync(fp);
    const c = cache[rp];
    if (c && c.mtime === s.mtimeMs) results.push({file:rp, symbols:c.symbols, mtime:s.mtimeMs});
    else {
      const sf = project.addSourceFileAtPath(fp);
      const symbols: SymbolInfo[] = [];
      function visit(node: Node) {
        let name = ""; if("getName" in node && typeof node.getName==="function") name=node.getName()||"";
        if(!name){node.forEachChild(c=>visit(c));return;}
        let kind:string|null=null, exported=false, isReact=false, isHook=false;
        if(Node.isFunctionDeclaration(node)){kind="function";exported=node.getModifiers().some(m=>m.getKind()===SyntaxKind.ExportKeyword);if(name&&name[0]===name[0].toUpperCase())isReact=true;if(name.startsWith("use"))isHook=true;}
        else if(Node.isVariableDeclaration(node)){const init=node.getInitializer();if(Node.isArrowFunction(init)||Node.isFunctionExpression(init)){kind="function";if(name&&name[0]===name[0].toUpperCase())isReact=true;if(name.startsWith("use"))isHook=true;}else kind="variable";}
        else if(Node.isInterfaceDeclaration(node)){kind="interface";exported=true;}
        else if(Node.isTypeAliasDeclaration(node)){kind="type";exported=true;}
        if(kind)symbols.push({name,kind,file:rp,startLine:node.getStartLineNumber(),endLine:node.getEndLineNumber(),exported,isReactComponent:isReact,isHook});
        node.forEachChild(c=>visit(c));
      }
      visit(sf);
      results.push({file:rp,symbols,mtime:s.mtimeMs});
      cache[rp]={mtime:s.mtimeMs,symbols};
    }
  }
  writeFileSync(cacheFile, JSON.stringify(cache,null,2));
  console.log(JSON.stringify({files:results,totalFiles:results.length,totalSymbols:results.reduce((s,f)=>s+f.symbols.length,0)},null,2));
}
main().catch(console.error);
