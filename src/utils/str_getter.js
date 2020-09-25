str_props = Object.getOwnPropertyNames(String);
for(name of str_props){
  print(name);
}

str_props = Object.getOwnPropertyNames(String.prototype);
for(name of str_props){
  print(name);
}
