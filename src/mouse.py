from terminal import run

def move_to(x:int, y:int) -> None:
    try:
        run(f'hyprctl dispatch movecursor {str(x)} {str(y)}')
    except Exception as e:
        print(f'Could not move cursor to {str(x)}, {str(y)}.')
        raise e

def click(button:str='left') -> None:
    try:
        code = '0xC0'
        match button.lower():
            case 'left': code = '0xC0'
            case 'right': code = '0xC1'
            case 'middle': code = '0xC2'
        run(f'ydotool click {code}')
    except Exception as e:
        print('Could not click at the cursor position.')
        raise e

def click_at(x:int, y:int, button:str='left') -> None:
    try:
        move_to(x=x, y=y)
        click(button=button)
    except Exception as e:
        print(f'Could not move to then click on {str(x)}, {str(y)}.')
        raise e