/*eslint-env node */
const CopyWebpackPlugin = require('copy-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: {
    main: './js/entry.js',
    aerials: './js/aerials.js',
    corrections: './corrections/corrections.js'
  },
  devtool: '#cheap-module-source-map',
  output: {
    path: __dirname + '/dist',
    filename: '[name].js'
  },
  externals: {
    // require("jquery") is external and available
    //  on the global var jQuery
    "jquery": "jQuery"
  },
  module: {
    loaders: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        loader: 'babel',
        query: {
          presets: ['es2015']
        }
      }
    ]
  },
  plugins: [
    new CopyWebpackPlugin(
      [
        { from: '+(images|styles)/**/+(*.css|*.gif|*.jpg|*.png|*.woff|*.tff|*.eot|*.less|*.scss)' },
        { from: 'js/vendor/*.js' },
        { from: 'corrections/+(*.css|*.png|ids.js)' },
        { from: 'about.html' },
        { from: 'terms.pdf' }
      ]
    ),
    new HtmlWebpackPlugin({
      chunks: ['main'],
      filename: 'index.html',
      hash: true,
      template: 'index.html',
      templateParameters: {
        apikey: process.env.GMAPS_API_KEY
      }
    }),
    new HtmlWebpackPlugin({
      chunks: ['corrections'],
      filename: 'corrections/index.html',
      hash: true,
      template: 'corrections/index.html'
    }),
    new HtmlWebpackPlugin({
      chunks: ['aerials'],
      filename: 'aerials.html',
      hash: true,
      template: 'aerials.html'
    })
  ]
};
