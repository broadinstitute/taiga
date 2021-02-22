import * as React from "react";
import {
  Modal,
  Button,
  FormGroup,
  FormControl,
  FormControlProps,
  ControlLabel,
  HelpBlock,
} from "react-bootstrap";

import TaigaApi from "../../models/api";
import { ArticleInfo } from "../../models/figshare";

enum ArticleIdStepError {
  ArticleUpdateForbidden,
  ArticleDoesNotExist,
}

interface ArticleIdStepProps {
  tapi: TaigaApi;
  handleFetchFigshareArticleSuccess: (figshareArticleInfo: ArticleInfo) => void;
}

interface ArticleIdStepState {
  articleId: string;
  loading: boolean;
  error: ArticleIdStepError;
}

export default class ArticleIdStep extends React.Component<
  ArticleIdStepProps,
  ArticleIdStepState
> {
  constructor(props: ArticleIdStepProps) {
    super(props);

    this.state = {
      articleId: "",
      loading: false,
      error: null,
    };
  }

  handleArticleIdChange = (
    e: React.FormEvent<FormControl & FormControlProps>
  ) => {
    this.setState({
      articleId: e.currentTarget.value as string,
      error: null,
    });
  };

  handleFetchFigshareArticle = () => {
    this.setState({ loading: true }, () => {
      this.props.tapi
        .get_figshare_article(parseInt(this.state.articleId))
        .then(this.props.handleFetchFigshareArticleSuccess)
        .catch((reason: Error) => {
          if (reason.message == "NOT FOUND") {
            this.setState({
              error: ArticleIdStepError.ArticleDoesNotExist,
              loading: false,
            });
          } else if ("Forbidden" in reason) {
            this.setState({
              error: ArticleIdStepError.ArticleUpdateForbidden,
              loading: false,
            });
          } else {
            console.log(reason);
          }
        });
    });
  };

  render() {
    return (
      <>
        <Modal.Body
          // @ts-expect-error
          bsClass="modal-body figshare-modal-body"
        >
          <FormGroup
            controlId="publicArticleId"
            validationState={this.state.error ? "error" : null}
          >
            <ControlLabel>Figshare article ID</ControlLabel>
            <FormControl
              type="text"
              value={this.state.articleId}
              onChange={this.handleArticleIdChange}
              disabled={this.state.loading}
            />
            <FormControl.Feedback />
            {this.state.error == ArticleIdStepError.ArticleUpdateForbidden && (
              <HelpBlock>
                The Figshare account linked to your Taiga account does not have
                permission to update this article. Please connect your Taiga
                account with Figshare account that does, or try a different
                article.
              </HelpBlock>
            )}
            {this.state.error == ArticleIdStepError.ArticleDoesNotExist && (
              <HelpBlock>No editable article was found for this ID</HelpBlock>
            )}
            <HelpBlock>
              The number after the article name in the public Figshare URL. For
              example, 11384241 for
              https://figshare.com/articles/DepMap_19Q4_Public/11384241
            </HelpBlock>
          </FormGroup>
        </Modal.Body>
        <Modal.Footer>
          <Button
            bsStyle="primary"
            disabled={!this.state.articleId || this.state.loading}
            onClick={this.handleFetchFigshareArticle}
          >
            Next
          </Button>
        </Modal.Footer>
      </>
    );
  }
}
