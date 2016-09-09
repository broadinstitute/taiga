/**
 * @author Juliano Castilho <julianocomg@gmail.com>
 */

import * as React from "react";

interface IAffixWrapperProps {
    offset : number
    key?: string
    className: string
    children?: any[]
}

interface IAffixState {
  affix : boolean
}

export class AffixWrapper extends React.Component<IAffixWrapperProps, IAffixState> {
  constructor(props: IAffixWrapperProps) {
      super(props);
      this.state = {affix: false}
  }
  
  handleScroll() {
    var affix = this.state.affix;
    var offset = this.props.offset;
    var scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    
    console.log("affix", affix, "offset", offset, "scrollTop", scrollTop)

    if (!affix && scrollTop >= offset) {
      this.setState({
        affix: true
      });
    }

    if (affix && scrollTop < offset) {
      this.setState({
        affix: false
      });
    }
  }

  componentDidMount() {
    window.addEventListener('scroll', this.handleScroll.bind(this));
  }

  componentWillUnmount() {
    window.removeEventListener('scroll', this.handleScroll.bind(this));
  }

  render() {
    var affix = this.state.affix ? ' affix' : ' affix-top';
    return (
      <div className={this.props.className+affix}>
        {this.props.children}
      </div>
    );
  }
}

