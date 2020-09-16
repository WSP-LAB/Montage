const crypto = require('crypto');
const escodegen = require('escodegen');
const fs = require('fs');
const path = require('path');


function extract_name(ast_path){
  start = ast_path.lastIndexOf('/') + 1;
  end = ast_path.lastIndexOf('.');
  hash = ast_path.slice(start, end);
  jsname = hash + '.js';
  return jsname
}

function generate_code(ast_path){
  ast = read_file(ast_path);
  ast = JSON.parse(ast);
  code = escodegen.generate(ast);
  return code;
}

function read_file(ast_path){
  return fs.readFileSync(ast_path, 'utf8');
}

function write_file(des_path, ast_path, code){
  jsname = extract_name(ast_path);
  js_path = path.join(des_path, jsname);
  fs.writeFileSync(js_path, code);
  return js_path
}

des_path = process.argv[2];

process.stdin.setEncoding('utf8');
process.stdin.on('data', function (ast_path) {
  try {
      ast_path = ast_path.trim();
      code = generate_code(ast_path);
      js_path = write_file(des_path, ast_path, code);
      process.stdout.write(js_path + '\n');
  } catch (err) {
    err = '[!] Error - ' + err + '\n';
    process.stdout.write(err);
  }
});
