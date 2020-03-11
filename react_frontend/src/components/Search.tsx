import * as React from "react";

import {
  Glyphicon,
  Form,
  FormGroup,
  ControlLabel,
  FormControl,
  Button
} from "react-bootstrap";

interface SearchInputProps {
  onKeyPress: (event: any, searchQuery: any) => void;
  onClick: (searchQuery: any) => void;
}

interface SearchInputState {
  searchQuery: string;
}

export class SearchInput extends React.Component<
  SearchInputProps,
  SearchInputState
> {
  state = {
    searchQuery: ""
  };

  handleChangeSearchQuery(e: any) {
    this.setState({
      searchQuery: e.target.value
    });
  }

  render() {
    return (
      <Form
        inline
        onSubmit={e => {
          e.preventDefault();
        }}
      >
        <FormGroup controlId="formInlineSearch">
          <FormControl
            type="text"
            placeholder="Search by name"
            value={this.state.searchQuery}
            onChange={event => this.handleChangeSearchQuery(event)}
            onKeyPress={event =>
              this.props.onKeyPress(event, this.state.searchQuery)
            }
          />
        </FormGroup>{" "}
        <Button
          type="button"
          onClick={() => this.props.onClick(this.state.searchQuery)}
        >
          Search
        </Button>
      </Form>
    );
  }
}
