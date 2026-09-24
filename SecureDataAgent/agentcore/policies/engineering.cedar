// Engineering Policy:
// Permit users in the "engineering" department to read S3 files under engineering/*

permit (
    principal,
    action == AgentCore::Action::"DataApiTarget___read_file",
    resource
)
when {
    principal has tag "department" &&
    principal.getTag("department") == "engineering" &&
    context.input.key startsWith "engineering/"
};

permit (
    principal,
    action == AgentCore::Action::"DataApiTarget___list_files",
    resource
)
when {
    principal has tag "department" &&
    principal.getTag("department") == "engineering" &&
    context.input.prefix startsWith "engineering/"
};
