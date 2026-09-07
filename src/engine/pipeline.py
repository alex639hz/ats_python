import queue

from engine.utils import Utils


class Pipeline(queue.Queue):
    def __init__(self, size, title):
        self.pipeline: queue.Queue = queue.Queue(size)
        self.title = title

    def element_pop(self, block=False, timeout=0.0):
        element = self.pipeline.get(block, timeout)
        return element

    def element_pop_unstructured(self, block=False, timeout=0.0):
        element = self.element_pop(block, timeout)
        return (element["command"], element["payload"])

    def element_push(self, cmd, payload={}):
        element = Pipeline.element_build(cmd, payload)
        self.pipeline.put(element)

    def get_pipe(self):
        return self.pipeline

    @staticmethod
    def element_build(cmd="", payload={}):
        return {
            "command": cmd,
            "payload": payload,
        }
