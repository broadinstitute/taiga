const merge = require("webpack-merge").merge;
const common = require("./webpack.common.js");
const ReactRefreshWebpackPlugin = require("@pmmmwh/react-refresh-webpack-plugin");
const ReactRefreshTypeScript = require("react-refresh-typescript");

const devConfig = (env, argv) => ({
  mode: "development",
  devtool: "cheap-module-source-map",

  output: {
    filename: "[name].js",
    publicPath: "http://localhost:5001/webpack",
  },

  devServer: {
    port: 5001,
    hot: true,
    client: {
      overlay: false,
      webSocketURL: "ws://localhost:5001/ws",
    },
    headers: {
      "Access-Control-Allow-Origin": "http://127.0.0.1:5000",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
      "Access-Control-Allow-Headers": "X-Requested-With, content-type, Authorization",
    },
  },

  plugins: [new ReactRefreshWebpackPlugin({ overlay: false })],

  module: {
    rules: [
      {
        test: /\.tsx?$/,
        exclude: /node_modules/,
        use: [
          {
            loader: require.resolve("ts-loader"),
            options: {
              transpileOnly: env.transpileOnly === "true",
              getCustomTransformers: () => ({
                before: [ReactRefreshTypeScript()],
              }),
            },
          },
        ],
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
                localIdentName: "[path][name]__[local]",
              },
            },
          },
          { loader: "sass-loader" },
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

module.exports = (env, argv) => merge(common, devConfig(env, argv));
