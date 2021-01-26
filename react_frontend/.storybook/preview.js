import * as React from "react";
import { addDecorator } from "@storybook/react";
import { MemoryRouter } from "react-router";

import "bootstrap/dist/css/bootstrap.min.css";
import "src/common/styles/base.css";

export const parameters = {
  actions: { argTypesRegex: "^on[A-Z].*" },
};

addDecorator((story) => (
  <MemoryRouter initialEntries={["/"]}>{story()}</MemoryRouter>
));
