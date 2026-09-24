// Finance Policy:
// Permit users in the "finance" department to read S3 files under finance/*
// and list files in finance/

permit (
    principal,
    action == AgentCore::Action::"DataApiTarget___read_file",
    resource
)
when {
    principal has tag "department" &&
    principal.getTag("department") == "finance" &&
    context.input.key startsWith "finance/"
};

permit (
    principal,
    action == AgentCore::Action::"DataApiTarget___list_files",
    resource
)
when {
    principal has tag "department" &&
    principal.getTag("department") == "finance" &&
    context.input.prefix startsWith "finance/"
};
