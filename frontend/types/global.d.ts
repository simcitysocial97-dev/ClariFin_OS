// Fix React 19 + Recharts type incompatibility
declare namespace React {
  interface CSSProperties {
    [key: `--${string}`]: string | number;
  }
}
