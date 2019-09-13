class InputManager:
    def __init__(self, input_state):
        self.input_state = input_state
    
        self.keystate = init_keystate()
