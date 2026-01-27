const webpack = require("webpack");
const path = require("path");

module.exports = {
  entry: {
    Taiga: {
      import: "./src/index.tsx",
      library: {
        type: "global",
        name: "[name]",
      },
    },
  },

  resolve: {
    // Add '.ts' and '.tsx' as resolvable extensions.
    extensions: [".ts", ".tsx", ".js", ".json"],
    fallback: {
      util: require.resolve("util/"), // polyfill Node util
      process: require.resolve("process/browser"),
    },
  },

  plugins: [
    new webpack.ProvidePlugin({ process: "process/browser" }),
  ],
};
