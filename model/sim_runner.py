import pandas as pd

from cadCAD import configs
from cadCAD.configuration import Experiment
from cadCAD.engine import ExecutionMode, ExecutionContext, Executor


def run(initial_state, partial_state_update_block, sim_configs):
    exp = Experiment()
    exp.append_configs(
        initial_state=initial_state,
        partial_state_update_blocks=partial_state_update_block,
        sim_configs=sim_configs
    )

    # Do not use multi_proc, breaks ipdb.set_trace()
    exec_mode = ExecutionMode()
    single_proc_context = ExecutionContext(exec_mode.single_proc)
    executor = Executor(single_proc_context, configs)

    raw_system_events, tensor_field, sessions = executor.execute()

    df = pd.DataFrame(raw_system_events)

    return df

