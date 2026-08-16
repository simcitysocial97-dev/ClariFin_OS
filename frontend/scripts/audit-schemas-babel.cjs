require('@babel/register')({
  extensions: ['.ts', '.js'],
  presets: [
    '@babel/preset-env',
    '@babel/preset-typescript'
  ]
})

require('./audit-schemas.cjs')
