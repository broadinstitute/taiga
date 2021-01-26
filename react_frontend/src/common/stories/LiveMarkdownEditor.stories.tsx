import * as React from "react";
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

const Wrapper = (props: WrapperProps) => {
  const [description, setDescription] = React.useState(props.description);
  return (
    <LiveMarkdownEditor
      onChange={(newDescription) => setDescription(newDescription)}
      description={description}
    />
  );
};
const Template: Story<WrapperProps> = (args: WrapperProps) => (
  <Wrapper {...args} />
);

export const Default = Template.bind({});

Default.args = {
  description: null,
} as WrapperProps;

export const ShowPreview = Template.bind({});

ShowPreview.args = {
  description: "sup",
  defaultShowPreview: true,
} as WrapperProps;
