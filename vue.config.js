module.exports = {
  transpileDependencies: true,
  publicPath: './',
  chainWebpack: config => {
    // 完全移除默认的 JSON 处理规则
    config.module.rules.delete('json');
    
    // 对 package.json 使用 json-loader
    config.module
      .rule('package-json')
      .test(/package\.json$/)
      .type('javascript/auto') // 关键：防止默认的 JSON 处理
      .use('json-loader')
      .loader('json-loader')
      .end();
    
    // 对 Mods 目录下的 JSON 文件使用 raw-loader
    config.module
      .rule('mods-json')
      .test(/assets[\\/]Mods[\\/].*\.json$/)
      .type('javascript/auto') // 关键：防止默认的 JSON 处理
      .use('raw-loader')
      .loader('raw-loader')
      .options({
        esModule: false
      })
      .end();
    
    // 对其他 JSON 文件使用 json-loader
    config.module
      .rule('other-json')
      .test(/\.json$/)
      .exclude
        .add(/package\.json$/)
        .add(/assets[\\/]Mods[\\/].*\.json$/)
        .end()
      .type('javascript/auto') // 关键：防止默认的 JSON 处理
      .use('json-loader')
      .loader('json-loader')
      .end();
    
    // 添加对文本文件的支持
    config.module
      .rule('text')
      .test(/\.(txt|config)$/)
      .use('raw-loader')
      .loader('raw-loader')
      .options({
        esModule: false
      })
      .end();
    
    // 添加对二进制文件的支持
    config.module
      .rule('binary')
      .test(/\.(exe|bin|dat)$/)
      .use('file-loader')
      .loader('file-loader')
      .options({
        name: '[path][name].[ext]',
        esModule: false
      })
      .end();
  }
}
