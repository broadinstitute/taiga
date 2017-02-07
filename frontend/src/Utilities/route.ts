function fetchPrefix(){
    // If taigaPrefix exists in the global scope
    if(taigaPrefix){
        taigaRoute = taigaPrefix;
    }
    else {
        taigaRoute = '';
    }
    return taigaRoute;
}

export var taigaRoute:string = fetchPrefix();

function pathJoin(parts: Array<string>, sep?: string){
   var separator = sep || '/';
   var replace   = new RegExp(separator+'{1,}', 'g');
   return parts.join(separator).replace(replace, separator);
}

// TODO: We could also create a component RelativeLink which could wrap a <Link> Component and manage the relativePath
export function relativePath(relativePath: string) {
    return pathJoin([taigaRoute, relativePath]);
}