import React, { useState } from "react";
import { Story, Meta } from "@storybook/react/types-6-0";

import LiveMarkdownEditor from "src/common/components/LiveMarkdownEditor";

export default {
  title: "Common/LiveMarkdownEditor",
  component: LiveMarkdownEditor,
} as Meta;

type WrapperProps = Omit<
  React.ComponentProps<typeof LiveMarkdownEditor>,
  "onChange"
>;

const Template: Story<WrapperProps> = (args) => {
  const [description, setDescription] = useState(args.description);
  return (
    <LiveMarkdownEditor
      onChange={(newDescription) => setDescription(newDescription)}
      description={description}
      defaultShowPreview={args.defaultShowPreview}
    />
  );
};

export const Default = Template.bind({});

Default.args = {
  description: null,
} as WrapperProps;

export const ShowPreview = Template.bind({});

ShowPreview.args = {
  description: "sup",
  defaultShowPreview: true,
} as WrapperProps;
