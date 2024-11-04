<center>
<|navbar|lov=|>
</center>

# mine2sirius

<|layout|columns=50px 1fr 50px|columns[mobile]=1|
<||>
<|
    <|Conversion|expandable|expanded=False|hover_text=Convert manufacturer files into communtiy formats.|
<|{platform}|selector|lov=Linux;Windows;MacOS|dropdown|>
<|{content}|file_selector|label=Select File|extensions=*|drop_message=Drop Files for conversion here|multiple=True|on_action=print_content|>
<|Construct converter|button|on_action=File_Converter|>
<|Convert selected|button|on_action=pass|>
    |>
    
|>
<||>
|>

<|{selected_scenario}|scenario_selector|>
<|{selected_data_node}|data_node_selector|>
<|{selected_data_node}|data_node|>