import os

import torch


UNIGRAM1000_LIST = ['<blank>'] + [_.split()[0] for _ in open(os.path.join(os.path.dirname(__file__), "labels", "unigram1000_units.txt")).read().splitlines()] + ['<eos>']


# Writes list of objects (anything that can be converted to str) to a txt file, separated by "\n"s
def write_to_txt(obj_list, path):
    f = open(path, "w")
    for obj in obj_list:
        f.write(str(obj) + "\n")
    f.close()
    

def ids_to_str(token_ids, char_list):
    tokenid_as_list = list(map(int, token_ids))
    token_as_list = [char_list[idx] for idx in tokenid_as_list]
    return "".join(token_as_list).replace("<space>", " ")


def set_requires_grad(model, val):
    for p in model.parameters():
        p.requires_grad = val
        

def average_checkpoints(last):
    ### TESTING ###
    # states1 = torch.load('/checkpoints/andreaszinonos/vsr-asr-alex/lrs3_randinit_lr5em3_warmup40_150epochs_ravenmask_transf12layers_withctcinclunlabel_withattunlabel_pred2ablock1_single_unlabrelv0p8_v2a0p1_sepva_vrel0p3_drop0p1_av/epoch=149.ckpt')["state_dict"]
    # states1 = {k[6:]: v for k, v in states1.items() if k.startswith("model.")}
    ### TESTING ###

    avg = None
    for path in last:
        states = torch.load(path)["state_dict"]
        states = {k[6:]: v for k, v in states.items() if k.startswith("model.")}
        if avg is None:
            avg = states
        else:
            for k in avg.keys():
                avg[k] += states[k]

    # average
    for k in avg.keys():
        if avg[k] is not None:
            # if "out_layer" in k:  ### TESTING ###
                # avg[k] = states1[k]
            # elif avg[k].is_floating_point():
            if avg[k].is_floating_point():
                avg[k] /= len(last)
            else:
                avg[k] //= len(last)
    
    # for path in last:
    #     states = torch.load(path)["state_dict"]
    #     states = {k[6:]: v for k, v in states.items() if k.startswith("model.")}
    #     for k in avg.keys():
    #         if torch.mean(torch.abs(states[k] - avg[k]) / abs(avg[k])) > 1:
    #             print(k)

    # states1 = torch.load('/checkpoints/andreaszinonos/vsr-asr-alex/lrs3_randinit_lr5em3_warmup40_150epochs_ravenmask_transf12layers_withctcinclunlabel_withattunlabel_pred2ablock1_single_unlabrelv0p8_v2a0p1_sepva_vrel0p3_drop0p1_av/epoch=149.ckpt')["state_dict"]
    # states1 = {k[6:]: v for k, v in states1.items() if k.startswith("model.")}
    # states2 = torch.load('/checkpoints/andreaszinonos/vsr-asr-alex/lrs3_randinit_lr5em3_warmup40_150epochs_ravenmask_transf12layers_withctcinclunlabel_withattunlabel_pred2ablock1_single_unlabrelv0p8_v2a0p1_sepva_vrel0p3_drop0p1_av/epoch=148.ckpt')["state_dict"]
    # states2 = {k[6:]: v for k, v in states2.items() if k.startswith("model.")}
    # states3 = torch.load('/checkpoints/andreaszinonos/vsr-asr-alex/lrs3_randinit_lr5em3_warmup40_150epochs_ravenmask_transf12layers_withctcinclunlabel_withattunlabel_pred2ablock1_single_unlabrelv0p8_v2a0p1_sepva_vrel0p3_drop0p1_av/epoch=147.ckpt')["state_dict"]
    # states3 = {k[6:]: v for k, v in states3.items() if k.startswith("model.")}
    # for k in avg.keys():
    #     if torch.mean(torch.abs(states1[k] - states2[k]) / abs(states2[k])) > 1:
    #         print(k)

    return avg


# def get_param_groups(model, num_blocks, base_lr_enc, base_lr_other, lr_decay_rate, min_lr=1e-6):
#     param_groups = {}
#     layer_scales = list(lr_decay_rate ** (num_blocks - i - 1) for i in range(num_blocks))
    
#     for name, param in model.named_parameters():
#         if not param.requires_grad:
#             continue
        
#         if "encoder.after_norm" in name:
#             group_name = "after_norm"
#             base_lr = max(base_lr_enc, min_lr)
#         elif "encoder.embed" in name:
#             group_name = "embed"
#             base_lr = max(layer_scales[0] * base_lr_enc, min_lr)
#         elif "encoder.frontend" in name:
#             group_name = "frontend"
#             base_lr = max(layer_scales[0] * base_lr_enc, min_lr)
#         elif "encoder.encoders" in name:
#             group_id = int(name.split(".")[3])
#             group_name = f"block_{group_id}"
#             base_lr = max(layer_scales[group_id] * base_lr_enc, min_lr)
#         else:
#             assert not name.startswith("encoder")
#             group_name = "other"
#             base_lr = max(base_lr_other, min_lr)
        
#         if group_name not in param_groups:
#             param_groups[group_name] = {
#                 "name": group_name,
#                 "lr": base_lr,
#                 "params": []
#             }
#         param_groups[group_name]["params"].append(param)
    
#     return list(param_groups.values())

def get_param_groups(model, num_blocks, base_lr_enc, base_lr_other, lr_decay_rate, min_lr=1e-6):
    param_groups = {}
    layer_scales = list(lr_decay_rate ** (num_blocks - i - 1) for i in range(num_blocks))
    
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        
        if "backbone.encoder.after_norm" in name:
            group_name = "after_norm"
            base_lr = max(base_lr_enc, min_lr)
        elif "backbone.encoder.embed" in name:
            group_name = "embed"
            base_lr = max(layer_scales[0] * base_lr_enc, min_lr)
        elif "backbone.encoder.frontend" in name or "backbone.encoder.linear" in name:
            group_name = "frontend"
            base_lr = max(layer_scales[0] * base_lr_enc, min_lr)
        elif "backbone.encoder.encoders" in name:
            group_id = int(name.split(".")[3])
            group_name = f"block_{group_id}"
            base_lr = max(layer_scales[group_id] * base_lr_enc, min_lr)
        else:
            assert not name.startswith("backbone.encoder")
            if name.startswith("target_backbone"):
                print(name)
            group_name = "other"
            base_lr = max(base_lr_other, min_lr)
        
        if group_name not in param_groups:
            param_groups[group_name] = {
                "name": group_name,
                "lr": base_lr,
                "params": []
            }
        param_groups[group_name]["params"].append(param)
    
    return list(param_groups.values())


def get_param_groups_ft(model, num_blocks, base_lr_enc, base_lr_other, lr_decay_rate, min_lr=1e-6):
    param_groups = {}
    layer_scales = list(lr_decay_rate ** (num_blocks - i - 1) for i in range(num_blocks))
    
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        
        if "encoder.after_norm" in name:
            group_name = "after_norm"
            base_lr = max(base_lr_enc, min_lr)
        elif "encoder.embed" in name:
            group_name = "embed"
            base_lr = max(layer_scales[0] * base_lr_enc, min_lr)
        elif "encoder.frontend" in name or "encoder.linear" in name:
            group_name = "frontend"
            base_lr = max(layer_scales[0] * base_lr_enc, min_lr)
        elif "encoder.encoders" in name:
            group_id = int(name.split(".")[3])
            group_name = f"block_{group_id}"
            base_lr = max(layer_scales[group_id] * base_lr_enc, min_lr)
        else:
            assert not name.startswith("encoder")
            group_name = "other"
            base_lr = max(base_lr_other, min_lr)
        
        if group_name not in param_groups:
            param_groups[group_name] = {
                "name": group_name,
                "lr": base_lr,
                "params": []
            }
        param_groups[group_name]["params"].append(param)
    
    return list(param_groups.values())