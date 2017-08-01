import * as React from "react";

import {Glyphicon} from "react-bootstrap";

interface StarFavoriteProps {
    onFavoriteClick: Function
    isFavorite: Boolean
}

interface StarFavoriteState {
    glyphStyle: string
}

const starStyle = {
    color: "#FFDF00"
};

const fullStarGlyph = "star";
const emptyStarGlyph = "star-empty";

export class StarFavorite extends React.Component<StarFavoriteProps, StarFavoriteState> {
    initStarGlyph() {
        if (this.props.isFavorite) {
            this.setState({
                glyphStyle: fullStarGlyph
            })
        }
        else {
            this.setState({
                glyphStyle: emptyStarGlyph
            })
        }
    }

    componentWillMount() {
        this.initStarGlyph();
    }

    toggleStarGlyph() {
        if (this.props.isFavorite) {
            this.setState({
                glyphStyle: emptyStarGlyph
            })
        }
        else {
            this.setState({
                glyphStyle: fullStarGlyph
            })
        }
    }

    overed(e) {
        this.toggleStarGlyph();
    }

    out(e) {
        this.initStarGlyph();
    }

    clicked(e) {
        this.props.onFavoriteClick(e);
    }

    render() {
        return <Glyphicon glyph={this.state.glyphStyle} style={starStyle}
                          onMouseOver={ (e) => this.overed(e)}
                          onMouseOut={ (e) => this.out(e) }
                          onClick={ (e) => this.clicked(e) }
        />
    }
}