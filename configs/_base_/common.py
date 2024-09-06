seed = 2023
num_k_samples = 25

generation_config = dict(
    max_new_tokens=25,
    min_new_tokens=5,
    top_p=0.9,
    do_sample=True,
)

neg_prompts = [
    "The following text is evil, abusive, harmful, negative, obscene, racist, rude and toxic: ",
]
#
pos_prompts = [
    "The following text is kind, civilized, polite, positive, respectful and supportive: "

]
# "Continue writing the following text as civilized, polite, and positivel"
# "The following text is kind, polite, positive, respectful and supportive: ",
#