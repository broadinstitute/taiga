import * as React from "react";
import { RouteComponentProps } from "react-router";

import { LeftNav } from "./LeftNav";

import { TaigaApi } from "../models/api";
import { relativePath } from "../utilities/route";

interface FigshareConnectionProps extends RouteComponentProps {
  tapi: TaigaApi;
}

interface FigshareConnectionState {
  status: "IN PROGRESS" | "SUCCESS" | "FAILURE";
  oauthState: string;
  code: string;
}

function redirectHome() {
  setTimeout(() => window.location.assign(relativePath("")), 2000);
}

export default class FigshareConnectionView extends React.Component<
  FigshareConnectionProps,
  FigshareConnectionState
> {
  constructor(props: FigshareConnectionProps) {
    super(props);

    const searchParams = new URLSearchParams(this.props.location.search);

    this.state = {
      status: "IN PROGRESS",
      oauthState: searchParams.get("state"),
      code: searchParams.get("code"),
    };
  }

  componentDidMount() {
    const { oauthState, code } = this.state;
    this.props.tapi.authorize_figshare(oauthState, code).then(
      () => this.setState({ status: "SUCCESS" }, redirectHome),
      () => this.setState({ status: "FAILURE" }, redirectHome)
    );
  }

  render() {
    const { status } = this.state;
    let message = "";
    if (status == "IN PROGRESS") {
      message = "Connecting to Figshare.";
    } else if (status == "SUCCESS") {
      message = "Successfully connected to Figshare. Redirecting to home page.";
    } else {
      message = "Could not connect to Figshare. Redirecting to home page.";
    }

    return (
      <div>
        <LeftNav items={[]} />
        <div id="main-content">
          <h1>Figshare Connection</h1>
          <div>{message}</div>
        </div>
      </div>
    );
  }
}
