// HR Policy:
// Permit users in the "hr" department to read S3 files under hr/*

permit (
    principal,
    action == AgentCore::Action::"DataApiTarget___read_file",
    resource
)
when {
    principal has tag "department" &&
    principal.getTag("department") == "hr" &&
    context.input.key startsWith "hr/"
};

permit (
    principal,
    action == AgentCore::Action::"DataApiTarget___list_files",
    resource
)
when {
    principal has tag "department" &&
    principal.getTag("department") == "hr" &&
    context.input.prefix startsWith "hr/"
};
