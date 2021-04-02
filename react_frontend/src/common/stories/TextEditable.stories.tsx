import React, { useState } from "react";
import { Story, Meta } from "@storybook/react/types-6-0";

import TextEditable from "src/common/components/TextEditable";

export default {
  title: "Common/TextEditable",
  component: TextEditable,
} as Meta;

type WrapperProps = Omit<
  React.ComponentProps<typeof TextEditable>,
  "onConfirm"
>;

const Template: Story<WrapperProps> = (args) => {
  const { id, title, value: defaultValue } = args;
  const [value, setValue] = useState(defaultValue);
  return (
    <TextEditable
      id={id}
      title={title}
      value={value}
      onConfirm={(newVal) => {
        setValue(newVal);
      }}
    />
  );
};

export const Default = Template.bind({});

Default.args = {
  id: "default",
  title: "title",
  value: "default",
} as WrapperProps;
