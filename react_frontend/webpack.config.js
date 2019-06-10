var webpack = require('webpack');
var ManifestPlugin = require('webpack-manifest-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const path = require('path');

module.exports = {
    mode: 'development',
    entry: "./src/index.tsx",
    output: {
        filename: 'react_frontend.js',
        path: __dirname + "./../depmap/static/js",
        library: 'DepMap'
    },


    // Enable sourcemaps for debugging webpack's output.
    devtool: "source-map",

    resolve: {
        // Add '.ts' and '.tsx' as resolvable extensions.
        extensions: [".ts", ".tsx", ".js", ".json"]
    },

    module: {
        rules: [
            // All files with a '.ts' or '.tsx' extension will be handled by 'ts-loader'.
            { test: /\.tsx?$/, loader: "awesome-typescript-loader" },
            // All output '.js' files will have any sourcemaps re-processed by 'source-map-loader'.
            { enforce: "pre", test: /\.js$/, loader: "source-map-loader", exclude: ["/node_modules/"] },
            // the following are only needed for processing css, which we (currently) only do when running cosmos
            { test: /\.css$/, use: ['style-loader', 'css-loader'] },
            { test: /\.(ttf|otf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?|(jpg|gif)$/, loader: 'file-loader'},
            { test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/, loader: 'url-loader?limit=10000&mimetype=application/font-woff'},
        ],
    },

    // When importing a module whose path matches one of the following, just
    // assume a corresponding global variable exists and use that instead.
    // This is important because it allows us to avoid bundling all of our
    // dependencies, which allows browsers to cache those libraries between builds.
    externals: {
        "plotly.js": "Plotly",
        "react": "React",
        "react-dom": "ReactDOM",
        "react-table": "ReactTable",
    },
};
