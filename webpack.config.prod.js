const path = require("path");
const webpack = require('webpack');
var ManifestPlugin = require('webpack-manifest-plugin');

module.exports = {
    entry: {
        frontend: "./frontend/src/index.tsx",
    },
    output: {
        filename: '[name].js',
        path: path.join(__dirname + "/taiga2/static")
    },

    // Enable sourcemaps for debugging webpack's output.
    devtool: "source-map",
    // devServer: {
    //     inline: true
    // },

    resolve: {
        // Add '.ts' and '.tsx' as resolvable extensions.
        extensions: [".webpack.js", ".web.js", ".ts", ".tsx", ".js"]
    },

    module: {
        rules: [
            // All files with a '.ts' or '.tsx' extension will be handled by 'ts-loader'.
            { test: /\.tsx?$/, use: "awesome-typescript-loader" },
            { test: /\.json$/, use: "json-loader" },
            {
                enforce: 'pre',
                test: /\.js$/,
                exclude: ["/node_modules/", "/frontend/node_modules/"],
                use: "source-map-loader"
            }
        ],
    },


    // When importing a module whose path matches one of the following, just
    // assume a corresponding global variable exists and use that instead.
    // This is important because it allows us to avoid bundling all of our
    // dependencies, which allows browsers to cache those libraries between builds.
    externals: {
        "react": "React",
        "react-dom": "ReactDOM",
        "react-router": "ReactRouter",
        "aws-sdk": "AWS",
        "react-bootstrap": "ReactBootstrap",
        "react-bootstrap-table": "ReactBootstrapTable"
    },

    plugins: [
    ]

};
