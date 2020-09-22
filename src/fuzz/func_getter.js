func_props = Object.getOwnPropertyNames(Function);
for(name of func_props){
  print(name);
}

func_props = Object.getOwnPropertyNames(Function.prototype);
for(name of func_props){
  print(name);
}
