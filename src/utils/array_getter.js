array_props = Object.getOwnPropertyNames(Array);
for(name of array_props){
  print(name);
}

array_props = Object.getOwnPropertyNames(Array.prototype);
for(name of array_props){
  print(name);
}
