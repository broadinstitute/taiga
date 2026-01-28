import * as React from "react";

interface NotFoundProps {
  message?: string;
}

export class NotFound extends React.Component<NotFoundProps, any> {
  componentDidMount() {
    document.title = "Not Found - Taiga";
  }

  render() {
    return (
      <div className="notFound">
        <h1>Not found :(</h1>
        <p>{this.props.message}</p>
      </div>
    );
  }
}
