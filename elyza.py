import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
DEFAULT_SYSTEM_PROMPT = "あなたは誠実で優秀な日本人のアシスタントです。"
text = "クマが海辺に行ってアザラシと友達になり、最終的には家に帰るというプロットの短編小説を書いてください。"

model_name = "elyza/ELYZA-japanese-Llama-2-7b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto")

if torch.cuda.is_available():
    model = model.to("cuda")
# Check that MPS is available
elif not torch.backends.mps.is_available():
    if not torch.backends.mps.is_built():
        print(
            "MPS not available because the current PyTorch install was not "
            "built with MPS enabled."
        )
    else:
        print(
            "MPS not available because the current MacOS version is not 12.3+ "
            "and/or you do not have an MPS-enabled device on this machine."
        )
else:
    mps_device = torch.device("mps")
    model = model.to(mps_device)


prompt = "{bos_token}{b_inst} {system}{prompt} {e_inst} ".format(
    bos_token=tokenizer.bos_token,
    b_inst=B_INST,
    system=f"{B_SYS}{DEFAULT_SYSTEM_PROMPT}{E_SYS}",
    prompt=text,
    e_inst=E_INST,
)


with torch.no_grad():
    token_ids = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")

    output_ids = model.generate(
        token_ids.to(model.device),
        max_new_tokens=256,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
output = tokenizer.decode(
    output_ids.tolist()[0][token_ids.size(1) :], skip_special_tokens=True
)
print(output)
"""
承知しました。以下にクマが海辺に行ってアザラシと友達になり、最終的には家に帰るというプロットの短編小説を記述します。

クマは山の中でゆっくりと眠っていた。
その眠りに落ちたクマは、夢の中で海辺を歩いていた。
そこにはアザラシがいた。
クマはアザラシに話しかける。

「おはよう」とクマが言うと、アザラシは驚いたように顔を上げた。
「あ、こんにちは」アザラシは答えた。
クマはアザラシと友達になりたいと思う。

「私はクマと申します。」クマは...
"""
