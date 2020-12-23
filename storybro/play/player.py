from __future__ import unicode_literals

import argparse
import sys
import textwrap

import cmd2
from cmd2 import with_argparser
from importlib_resources import read_text
from shutil import copyfile
from storybro.story.utils import console_print, get_num_options, player_died, player_won, get_similarity, \
    first_to_second_person, YAML_FILE
        
from storybro.generation.gpt2.generator import GPT2Generator
from storybro.models.model import Model
from storybro.play.block_formatter import BlockFormatter
from storybro.play.settings import PlayerSettings
from storybro.stories.block import Block
from storybro.stories.story import Story
from storybro.utils import yes_no
import os
import sys
import os
from flask import Flask
from flask import request


app = Flask(__name__)

class NoBlockCommitter(Exception):
    message = "No BlockCommitter set for Player."

import shutil
theself = None
class Player(cmd2.Cmd):
    """A simple cmd2 application."""

    def __init__(self, resolved, model: Model, story: Story, settings: PlayerSettings,
                 block_formatter: BlockFormatter):
        global theself
        super().__init__()
        self.results = []
        self.model: Model = model
        self.story: Story = story
        self.resolved = resolved
        print(self.story)
        self.settings: PlayerSettings = settings
        self.block_formatter: BlockFormatter = block_formatter

        self.generator: GPT2Generator = None
        self.pending = []
        self.remove_default_commands()
        self.setup_settables()
        self.allow_ansi = "Terminal"
        self.display_splash()
        self.generator = self.setup_generator(self.model)
        self.doing = False
        theself = self
        app.run(debug=False, host="0.0.0.0", port="8088")
    @property
    def prompt(self):
        return f"{self.settings.icon_for_input}   "

    def remove_default_commands(self):
        del cmd2.Cmd.do_alias
        del cmd2.Cmd.do_edit
        del cmd2.Cmd.do_history
        del cmd2.Cmd.do_macro
        del cmd2.Cmd.do_py
        del cmd2.Cmd.do_run_pyscript
        del cmd2.Cmd.do_run_script
        del cmd2.Cmd.do_shell
        del cmd2.Cmd.do_shortcuts

    def setup_generator(self, model):
        return GPT2Generator(model, self.resolved)

    def setup_settables(self):
        """Create pass-through properties on Player class for each setting in PlayerSettings"""
        self.settable = self.settings.settable()
        for attr in self.settable:
            if not hasattr(self, attr):
                setattr(Player, attr, property(
                    lambda self, attr=attr: getattr(self.settings, attr),
                    lambda self, value, attr=attr: setattr(self.settings, attr, value)))

    def display_splash(self):
        text = read_text('storybro.data', 'splash.txt')
        text += f"\n\n🕑 Initializing `{self.model.name}` model; Please wait..."
        self.poutput(text)

    def run(self):
        self.display_splash()
        #self.generator = self.setup_generator(self.model)

        #if self.story.blocks:
        #    self.poutput(self.block_formatter.render_story(self.story))

        #sys.exit(self.cmdloop())

    def _input_line_to_statement(self, line: str) -> cmd2.Statement:
        line = line.strip()

        if line == "eof":
            line = "quit"
        elif not line.startswith("/"):
            line = f"commit {line}"
        else:
           line = line[1:]

        return super()._input_line_to_statement(line)
    
    @app.route('/play',methods = ['POST', 'GET'])
    def play():
        global theself
        
                #time.sleep(5*60)
        try:
            if theself.doing == True:
                return('Whoa down cowboy! At present GPU capabilities (only 1x 8gb) this game can only handle ONE request at a time!')

            else:
                theself.doing = True
                print("🕑", end="\r")

                input_text = request.args.get("harhar")#input("> ").strip()#['data'][0]['comment']['comment']
                print(input_text)
                input_block = Block(input_text, attrs=dict(type='input'))
                input_block: Block = theself.block_formatter.filter_block(input_block)
                if input_block.text:
                    theself.story.blocks.append(input_block)

                processed_story: str = theself.block_formatter.process_story(theself.story)
                output_text: str = theself.generator.generate_raw(processed_story)
                """
                for i in output_text:
                    if len(theself.story.blocks) >= 3:
                        for a in range(2,4):
                            similarity = get_similarity(
                                theself.results[-1], theself.results[-a]
                            )
                            if similarity > 0.9:
                                output_text.remove(output_text[i])
                                console_print(
                                    "Woops that action caused the model to start looping. Try a different action to prevent that."
                                )    
                    if len(output_text) < 8:
                        print('less than 8 char, removing..')
                        output_text.remove(output_text[i])
                ran = None
                while ran == None:
                    try:
                        ran = random.randint(0, len(output_text))
                    except:
                        ran = None
                print('lenoutput ' + str(len(output_text)))
                output_text = output_text[ran]
                """
                theself.doing = False
                output_block = Block(output_text, attrs=dict(type='output'))
                output_block = theself.block_formatter.filter_block(output_block)
                theself.story.blocks.append(output_block)
                #if len(theself.story.blocks) > 3:
                #    theself.story.blocks.pop(0)
                #    theself.story.blocks.pop(0)
                print("  ", end="\r")
                
                rendered_block: Block = theself.block_formatter.render_block(output_block)
                theself.results.append(rendered_block.text)
                print(theself.results)
                return (rendered_block.text)
            #else
        except Exception as e:
            print(e)
            


    def do_save(self, text):
        self.story.save()
        self.poutput(f"Story saved: {self.story.path}.")

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-l', '--last-n', type=int, default=0, help='print the last [n] blocks')
    @with_argparser(argparser)
    def do_print(self, args):
        if self.story.blocks:
            self.poutput(self.block_formatter.render_story(self.story, args.last_n))

    def format_block_for_list(self, block, index, index_width):
        if block.attrs.get('type') == 'input':
            icon = self.settings.icon_for_input
        else:
            icon = self.settings.icon_for_output

        if block.attrs.get('pinned'):
            pin = self.settings.icon_for_pins
        else:
            pin = "  "

        index_label = str(index).rjust(index_width)

        text = block.text

        if self.settings.fill_width:
            text = textwrap.shorten(text, self.settings.fill_width, placeholder="")

        return f"{icon}{pin} {index_label}: {text}"

    argparser = argparse.ArgumentParser()
    argparser.add_argument('indices', nargs='*', default=None, type=int)
    argparser.add_argument('-r', '--range', help="list the blocks in range", default=None, required=False)
    argparser.add_argument('-l', '--last_n', help="list the last n blocks", type=int, default=0, required=False)
    argparser.add_argument('-f', '--first_n', help="list the first n blocks", type=int, default=0, required=False)
    @with_argparser(argparser)
    def do_list(self, args):
        filtered = self.story.filter_blocks(args.indices or None,
                                            args.first_n or None,
                                            args.last_n or None,
                                            args.range)
        n_blocks = len(self.story.blocks)
        index_width = len(f"{n_blocks}")

        for index, block in enumerate(self.story.blocks):
            if block in filtered:
                block_line = self.format_block_for_list(block, index, index_width)
                self.poutput(block_line)

    argparser = argparse.ArgumentParser()
    argparser.add_argument('indices', nargs='*', default=None, type=int)
    argparser.add_argument('-r', '--range', help="list the blocks in range", default=None, required=False)
    argparser.add_argument('-l', '--last_n', help="list the last n blocks", type=int, default=0, required=False)
    argparser.add_argument('-f', '--first_n', help="list the first n blocks", type=int, default=0, required=False)
    @with_argparser(argparser)
    def do_delete(self, args):
        filtered = self.story.filter_blocks(args.indices or None,
                                            args.first_n or None,
                                            args.last_n or None,
                                            args.range)
        n_blocks = len(self.story.blocks)
        index_width = len(f"{n_blocks}")

        for index, block in enumerate(self.story.blocks):
            prefix = "❌" if block in filtered else "  "
            block_line = self.format_block_for_list(block, index, index_width)
            self.poutput(f"{prefix}{block_line}")

        message = f"Delete these {len(filtered)} blocks?" if len(filtered) > 1 else "Delete this block?"
        if yes_no(message):
            for block in filtered:
                self.story.blocks.remove(block)

            self.poutput("Done.")

    argparser = argparse.ArgumentParser()
    argparser.add_argument('indices', nargs='*', default=None, type=int)
    argparser.add_argument('-r', '--range', help="list the blocks in range", default=None, required=False)
    argparser.add_argument('-l', '--last_n', help="list the last n blocks", type=int, default=0, required=False)
    argparser.add_argument('-f', '--first_n', help="list the first n blocks", type=int, default=0, required=False)
    @with_argparser(argparser)
    def do_pin(self, args):
        filtered = self.story.filter_blocks(args.indices or None,
                                            args.first_n or None,
                                            args.last_n or None,
                                            args.range)
        n_blocks = len(self.story.blocks)
        index_width = len(f"{n_blocks}")

        for index, block in enumerate(self.story.blocks):
            if block.attrs.get('pinned'):
                continue

            prefix = self.settings.icon_for_pins if block in filtered else "  "
            block_line = self.format_block_for_list(block, index, index_width)
            self.poutput(f"{prefix}{block_line}")

        message = f"Pin these {len(filtered)} blocks?" if len(filtered) > 1 else "Pin this block?"
        if yes_no(message):
            for block in filtered:
                block.attrs['pinned'] = True

            self.poutput("Done.")

    argparser = argparse.ArgumentParser()
    argparser.add_argument('indices', nargs='*', default=None, type=int)
    argparser.add_argument('-r', '--range', help="list the blocks in range", default=None, required=False)
    argparser.add_argument('-l', '--last_n', help="list the last n blocks", type=int, default=0, required=False)
    argparser.add_argument('-f', '--first_n', help="list the first n blocks", type=int, default=0, required=False)
    @with_argparser(argparser)
    def do_unpin(self, args):
        filtered = self.story.filter_blocks(args.indices or None,
                                            args.first_n or None,
                                            args.last_n or None,
                                            args.range)
        n_blocks = len(self.story.blocks)
        index_width = len(f"{n_blocks}")

        for index, block in enumerate(self.story.blocks):
            if not block.attrs.get('pinned'):
                continue

            prefix = "❌" if block in filtered else "  "
            block_line = self.format_block_for_list(block, index, index_width)
            self.poutput(f"{prefix}{block_line}")

        message = f"Unpin these {len(filtered)} blocks?" if len(filtered) > 1 else "Unpin this block?"
        if yes_no(message):
            for block in filtered:
                del block.attrs['pinned']

            self.poutput("Done.")

    argparser = argparse.ArgumentParser()
    @with_argparser(argparser)
    def do_stats(self, args):
        inputs = 0
        outputs = 0
        pinned = 0
        total_words = 0
        total_characters = 0

        for block in self.story.blocks:
            if block.attrs.get('type') == 'input':
                inputs += 1
            else:
                outputs += 1

            if block.attrs.get('pinned'):
                pinned += 1

            total_characters += len(block.text)
            total_words += len(block.text.split())

        self.poutput("Story stats:")
        self.poutput(f" - Inputs: {inputs}")
        self.poutput(f" - Outputs: {outputs}")
        self.poutput(f" - Pinned: {pinned}")
        self.poutput(f" - Words: {total_words}")
        self.poutput(f" - Characters: {total_characters}")
    def do_commit(self, input_text: str):
        print("🕑", end="\r")
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")