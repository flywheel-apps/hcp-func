"""
This is a module with specific functions for the HCP Functional Pipeline
"""
import glob
import os
import os.path as op


def remove_intermediate_files(context):
    """
    Delete extraneous files used for the diffusion processing
    """
    # Delete extraneous processing files
    config = context.config
    for dir in ["prevols", "postvols"]:
        try:
            shutil.rmtree(
                op.join(
                    context.work_dir,
                    config["Subject"],
                    config["fMRIName"],
                    "OneStepResampling",
                    dir,
                )
            )
        except:
            pass

    del_niftis = glob.glob(
        op.join(
            context.work_dir,
            config["Subject"],
            config["fMRIName"],
            "MotionMatrices",
            "*.nii.gz",
        )
    )

    try:
        for nifti in del_niftis:
            os.remove(nifti)
    except:
        pass


def configs_to_export(context):
    """
    Export HCP Functional Pipeline configuration into the Subject directory
    Return the config and filename
    """
    config = {}
    hcpfunc_config = {"config": config}
    for key in [
        "RegName",
        "Subject",
        "fMRIName",
        "BiasCorrection",
        "MotionCorrection",
        "AnatomyRegDOF",
    ]:
        if key in context.config.keys():
            config[key] = context.config[key]

    config["FinalfMRIResolution"] = context.gear_dict["Surf-params"]["fmrires"]
    config["GrayordinatesResolution"] = context.gear_dict["Surf-params"][
        "grayordinatesres"
    ]
    config["LowResMesh"] = context.gear_dict["Surf-params"]["lowresmesh"]
    config["SmoothingFWHM"] = context.gear_dict["Surf-params"]["smoothingFWHM"]

    hcpfunc_config_filename = op.join(
        context.work_dir,
        context.config["Subject"],
        "{}_{}_hcpfunc_config.json".format(
            context.config["Subject"], context.config["fMRIName"]
        ),
    )

    return hcpfunc_config, hcpfunc_config_filename
