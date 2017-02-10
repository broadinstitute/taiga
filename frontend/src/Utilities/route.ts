function fetchPrefix(){
    // If taigaPrefix exists in the global scope
    if(taigaPrefix){
        return taigaPrefix;
    }
    else {
        return undefined;
    }
}

function fetchUserName() {
    // If taigaCurrentUserName exists in global scope
    if(taigaCurrentUserName) {
        console.log("User name is "+taigaCurrentUserName);
        return taigaCurrentUserName;
    }
    else {
        return undefined;
    }
}

function fetchUserEmail() {
    // If taigaCurrentUserEmail exists in global scope
    if(taigaCurrentUserEmail) {
        console.log("User email is "+taigaCurrentUserEmail);
        return taigaCurrentUserEmail;
    }
    else {
        return undefined;
    }
}

export var taigaRoute:string = fetchPrefix();

export var currentUserName:string = fetchUserName();

export var currentUserEmail:string = fetchUserEmail();

function pathJoin(parts: Array<string>, sep?: string){
   var separator = sep || '/';
   var replace   = new RegExp(separator+'{1,}', 'g');
   return parts.join(separator).replace(replace, separator);
}

// TODO: We could also create a component RelativeLink which could wrap a <Link> Component and manage the relativePath
export function relativePath(relativePath: string) {
    return pathJoin([taigaRoute, relativePath]);
}