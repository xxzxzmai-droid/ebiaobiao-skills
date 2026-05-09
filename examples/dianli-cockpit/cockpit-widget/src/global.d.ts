declare module '*.css' {
  const classes: Record<string, string>;
  export default classes;
}

declare const process: {
  env: {
    WIDGET_PACKAGE_ID?: string;
  };
};
