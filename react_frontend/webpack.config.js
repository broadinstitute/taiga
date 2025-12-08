const webpack = require("webpack");
const path = require("path");

module.exports = {
  mode: "development",

  entry: "./src/index.tsx",

  output: {
    filename: "react_frontend.js",
    path: path.resolve(__dirname, "../taiga2/static/js"),
    library: "Taiga",

    // Fix "digital envelope routines::unsupported" (MD4 removed in Node 20)
    hashFunction: "sha256",
  },

  // Enable sourcemaps for debugging webpack's output.
  devtool: "source-map",

  resolve: {
    // Add '.ts' and '.tsx' as resolvable extensions.
    extensions: [".ts", ".tsx", ".js", ".json"],
    fallback: {
      util: require.resolve("util/"), // polyfill Node util
      process: require.resolve("process/browser"),
    },
  },

  plugins: [
    new webpack.ProvidePlugin({
      process: "process/browser",
    }),
  ],

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
};
