const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = (env, argv) => {
  const isDevelopment = argv.mode === 'development';

  return {
    entry: './src/index.js', // Entry point for your app
    output: {
      filename: 'bundle.js', // Output bundle name
      path: path.resolve(__dirname, isDevelopment ? 'build' : 'dist'), // Output folder
      clean: true, // Clean output folder before building
    },
    devtool: isDevelopment ? 'eval-cheap-module-source-map' : 'source-map', // Enable source maps in dev mode
    devServer: {
      static: path.join(__dirname, 'src'), // Serve static files from 'src'
      port: 8080, // Specify the port
      open: true, // Automatically open the browser
      hot: true, // Enable Hot Module Replacement
      client: {
        overlay: true, // Show errors/warnings overlay in the browser
      },
    },
    module: {
      rules: [
        {
          test: /\.css$/i, // Handle CSS files
          use: ['style-loader', 'css-loader'], // Inject CSS into the DOM
        },
        {
          test: /\.js$/, // Handle JS files
          enforce: 'pre', // Preprocess files
          use: ['source-map-loader'], // Load source maps for debugging
          exclude: /node_modules/, // Exclude node_modules
        },
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './src/index.html', // Use the provided index.html as a template
        inject: 'body', // Inject the bundle at the end of the <body>
      }),
    ],
    resolve: {
      extensions: ['.js', '.css'], // Resolve file extensions
    },
    optimization: {
      minimize: !isDevelopment, // Minify code in production
    },
  };
};
