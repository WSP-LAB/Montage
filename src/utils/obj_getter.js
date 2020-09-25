obj_props = Object.getOwnPropertyNames(Object);
for(name of obj_props){
  print(name);
}

obj_props = Object.getOwnPropertyNames(Object.prototype);
for(name of obj_props){
  print(name);
}
