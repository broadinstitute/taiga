function fetchPrefix(){
    // If taigaPrefix exists in the global scope
    if(taigaPrefix){
        return taigaPrefix;
    }
    else {
        return undefined;
    }
}

function fetchUserToken() {
    if(taigaUserToken) {
        console.log("User token is "+taigaUserToken);
        return taigaUserToken;
    }
    else {
        return undefined;
    }
}

export var taigaRoute:string = fetchPrefix();

export var currentUserToken:string = fetchUserToken();

function pathJoin(parts: Array<string>, sep?: string){
   var separator = sep || '/';
   var replace   = new RegExp(separator+'{1,}', 'g');
   return parts.join(separator).replace(replace, separator);
}

// TODO: We could also create a component RelativeLink which could wrap a <Link> Component and manage the relativePath
export function relativePath(relativePath: string) {
    return pathJoin([taigaRoute, relativePath]);
}