const path = require("path");
const merge = require("webpack-merge").merge;
const common = require("./webpack.common.js");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");
const { WebpackManifestPlugin } = require("webpack-manifest-plugin");

module.exports = merge(common, {
  mode: "production",
  devtool: "source-map",

  output: {
    filename: "[name].[contenthash].js",
    publicPath: "",
    path: path.resolve(__dirname, "../taiga2/static/webpack"),
  },

  plugins: [new WebpackManifestPlugin(), new CleanWebpackPlugin()],

  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: "ts-loader",
      },

      {
        enforce: "pre",
        test: /\.js$/,
        loader: "source-map-loader",
        exclude: /node_modules/,
      },

      // CSS
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },

      // SCSS
      {
        test: /\.scss$/,
        use: [
          "style-loader",
          {
            loader: "css-loader",
            options: {
              modules: {
                // https://webpack.js.org/loaders/css-loader/#localidentname
                // use '[hash:base64]' for production
                // use '[path][name]__[local]' for development
                localIdentName: "[hash:base64]",
                localIdentHashFunction: "md5",
              },
            },
          },
          {
            loader: "sass-loader",
            options: {
              webpackImporter: false,
            },
          },
        ],
      },

      // Webpack 5 asset modules replace file-loader + url-loader
      {
        test: /\.(png|jpg|gif|svg|ttf|otf|eot|woff|woff2)$/i,
        type: "asset",
        parser: {
          dataUrlCondition: {
            maxSize: 10 * 1024, // same behavior as old url-loader limit=10000
          },
        },
      },
    ],
  },
});
