// decorators: require('./components/decorators'),
// animations: require('./themes/animations'),
// theme: require('./themes/default')

declare module "react-treebeard" {
    import * as React from 'react';

    interface TreeBeardProps {
        style?: Object,
        data?: Object | Array<any>,
        animations?: Object | Boolean,
        onToggle?: Function,
        decorators?: Object
    }

    let TreeBeard: React.ClassicComponentClass<TreeBeardProps>;

    export default TreeBeard;
}