regexp_props = Object.getOwnPropertyNames(RegExp);
for(name of regexp_props){
  print(name);
}

regexp_props = Object.getOwnPropertyNames(RegExp.prototype);
for(name of regexp_props){
  print(name);
}
