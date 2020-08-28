const esprima = require('esprima');
const fs = require('fs');
const path = require('path');

function extract_name(path){
  idx = path.lastIndexOf('.');
  name = path.slice(0, idx) + '.json';
  return name;
}

function get_file_list(js_dir){
  return fs.readdirSync(js_dir);
}

function parse(src, des, file){
  ast_path = extract_name(file);
  ast_path = path.join(des, ast_path);
  js_path = path.join(src, file);
  code = read_file(js_path);

  try {
    parse_and_write(code, ast_path);
  } catch (err) {
    err_msg = '[!] Error - ' + js_path + '\n';
    err_msg += err
    console.log(err_msg);
  }
}

function parse_and_write(code, ast_path){
  ast = esprima.parse(code);
  ast = JSON.stringify(ast, null, 2);
  write_file(ast_path, ast);
}

function parse_single() {
  process.stdin.setEncoding("utf8");
  process.stdin.on('data', function (js_path) {
    js_path = js_path.trim();
    ast_path = extract_name(js_path);
    code = read_file(js_path);

    try{
      parse_and_write(code, ast_path);
      process.stdout.write(ast_path + '\n');
    } catch (err) {
      err_msg = '[!] Error - ' + js_path + '\n';
      err_msg += err
      process.stdout.write(err_msg);
    }
  });
}

function read_file(js_path){
  return fs.readFileSync(js_path, 'utf8');
}

function write_file(ast_path, ast){
  fs.writeFileSync(ast_path, ast);
}

if (process.argv.length == 4) {
 src = process.argv[2];
 des = process.argv[3];
 dir = true;
} else {
  dir = false;
}

if (dir) {
  js_list = get_file_list(src);

  for (file of js_list) {
    parse(src, des, file);
  }
} else {
  parse_single();
}
