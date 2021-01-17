import pandas as pd

from cadCAD import configs
from cadCAD.configuration import Experiment
from cadCAD.engine import ExecutionMode, ExecutionContext, Executor

from model.config import sim_config
from model.partial_state_update_block import partial_state_update_block
from model.genesis_states import *

def run():
    exp = Experiment()
    exp.append_configs(
        initial_state=initial_values,
        partial_state_update_blocks=partial_state_update_block,
        sim_configs=sim_config
    )

    # Do not use multi_proc, breaks ipdb.set_trace()
    exec_mode = ExecutionMode()
    single_proc_context = ExecutionContext(exec_mode.single_proc)
    executor = Executor(single_proc_context, configs)

    raw_system_events, tensor_field, sessions = executor.execute()

    df = pd.DataFrame(raw_system_events)

    return df


def postprocessing(df):


    return df