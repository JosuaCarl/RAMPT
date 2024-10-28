<center>
<|navbar|lov={[("/", "Application"), ("https://josuacarl.github.io/mine2sirius_pipe", "Documentation")]}|>
</center>

# mine2sirius

<|layout|columns=50px 1fr 50px|columns[mobile]=1|
    <||>
    <|Conversion|expandable|expanded=False|
        <|{content}|file_selector|label=Select File|extensions=None|drop_message=Drop Files for conversion here|multiple=True|>
        <|Convert selected|button|on_action={pass}|>
    |>
    <||>
|>

<|{selected_scenario}|scenario_selector|>
<|{selected_data_node}|data_node_selector|>
<|{selected_data_node}|data_node|>