declare let taigaPrefix: string;
declare let taigaUserToken: string;

export function getTaigaPrefix() {
  // If taigaPrefix exists in the global scope
  if (taigaPrefix) {
    return taigaPrefix;
  } else {
    return undefined;
  }
}

export function getUserToken() {
  return (window as any).taigaUserToken;
}

function pathJoin(parts: Array<string>, sep?: string) {
  var separator = sep || "/";
  var replace = new RegExp(separator + "{1,}", "g");
  return parts.join(separator).replace(replace, separator);
}

// TODO: We could also create a component RelativeLink which could wrap a <Link> Component and manage the relativePath
export function relativePath(relativePath: string) {
  return pathJoin([getTaigaPrefix(), relativePath]);
}
