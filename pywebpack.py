import os
import subprocess
import json
import psutil

from flask import Blueprint


class PyWebpack:

    def __init__(self, app, blueprints):

        self.base_directory = os.getcwd()
        self.npm_path = app.config['NPM_PATH']
        self.package_json = os.path.join(self.base_directory, 'package.json') \
            if os.path.isfile('package.json') else None

        self.blueprints = [blueprint for blueprint in blueprints]

        self.npm_init()
        self.register_blueprints()
        self.install_dependencies()

    def npm_init(self):

        if self.package_json is None:
            ini = open(f'{self.base_directory}/pywebpack/boilerplates/package.json.ini', 'r')
            ini_content = ini.read()

            with open('package.json', 'w') as p:
                p.write(ini_content)
                p.close()
            self.package_json = os.path.join(self.base_directory, 'package.json')

    def install_dependencies(self):
        if not self.check_dependencies():
            self.create_webpack_boilerplate()
            self.install_webpack_dependencies()
            self.install_sass_css_dependencies()
        self.create_webpack_boilerplate()

    def get_modules_json(self):
        file = open(self.package_json, 'r').read()
        package_dict = json.loads(file)
        dev_dependencies = package_dict['dependencies']
        dependencies = package_dict['devDependencies']
        return list(dependencies.keys()) + list(dev_dependencies.keys())

    def check_dependencies(self):
        if os.path.isdir('node_modules'):
            modules = os.listdir('node_modules')
            return all([True for item in self.get_modules_json() if item in modules])
        return False

    def register_blueprints(self):
        for blueprint in self.blueprints:
            BlueprintConfig(blueprint)

    def get_conf_json_from_blueprints(self):
        package_json_files = []

        for blueprint in self.blueprints:

            blueprint_path = blueprint.root_path

            package_json_path = os.path.join(blueprint_path, 'static_bp_one/conf.json')

            if os.path.isfile(package_json_path):
                with open(package_json_path, 'r') as j:
                    package_json = j.read()
                    package_json_files.append(package_json)
                    j.close()

        return package_json_files

    def create_webpack_boilerplate(self):

        package_json_files = self.get_conf_json_from_blueprints()

        boilerplate = open('pywebpack/boilerplates/webpack.config.ini', 'r')
        content = boilerplate.read()

        package_json = ','.join(package_json_files)
        content = content.format(package_json)

        with open('webpack.config.js', 'w') as wp:
            wp.write(content)

    def install_webpack_dependencies(self):
        subprocess.call([self.npm_path, 'install', 'webpack', 'webpack-cli', '--save-dev'])

    def install_sass_css_dependencies(self):
        subprocess.call([self.npm_path, 'install',
                         'sass',
                         'sass-loader',
                         'css-loader',
                         'mini-css-extract-plugin',
                         '--save-dev'])


    def build(self, mode='development'):

        if mode == 'production':
            subprocess.call([self.npm_path, 'run', 'build-prod'])
        else:
            if not self.webpack_is_running():
                subprocess.Popen(["start", "cmd", "/k", "npm run build-dev"], shell=True)

    def webpack_is_running(self):
        processes = [process for process in psutil.process_iter(['pid', 'name']) if process.as_dict(['name'])[
            'name'] == 'node.exe']

        processes_cwd = [process.as_dict(['cwd'])['cwd'] for process in processes]

        return self.base_directory in processes_cwd




class BlueprintConfig:

    def __init__(self, blueprint):
        self.blueprint = self.validate_blueprint(blueprint)
        self.blueprint_path = self.blueprint.root_path
        self.__blueprint_name = self.blueprint_name
        self.__blueprint_relative_path = self.blueprint_relative_path
        self.__boilerplate = self.boilerplate
        self.create_static_folder_tree()
        self.create_conf_json_for_blueprint()

    @property
    def blueprint_name(self):
        blueprint_parents = self.blueprint_path.split("\\")
        return blueprint_parents[-1]

    @property
    def blueprint_relative_path(self):
        blueprint_parents = self.blueprint_path.split("\\")
        return '/'.join(blueprint_parents[-2::])


    def validate_blueprint(self, blueprint):
        if isinstance(blueprint, Blueprint):
            return blueprint
        raise Exception('Argument is not a blueprint')

    @property
    def boilerplate(self):

        blueprint_parents = self.blueprint_path.split("\\")
        blueprint_abs_path = '/'.join(blueprint_parents)
  
        with open(f'pywebpack/boilerplates/conf.json.ini', 'r') as bp:

            self.__boilerplate = bp.read()
            self.__boilerplate = self.__boilerplate.replace('{blueprint_name}', self.blueprint_name)
            self.__boilerplate = self.__boilerplate.replace('{blueprint_relative_path}', self.__blueprint_relative_path)
            self.__boilerplate = self.__boilerplate.replace('{blueprint_abs_path}', blueprint_abs_path)

        return self.__boilerplate

    def create_conf_json_for_blueprint(self):
        with open(f'{self.blueprint_path}/static_bp_one/conf.json', 'w') as conf:
            conf.write(self.boilerplate)

    def create_static_folder_tree(self):
        static_folder = os.path.join(self.blueprint_path, 'static_bp_one/src')
        if not os.path.exists(static_folder):

            self.create_sub_folder(static_folder, 'js')
            self.create_file(f'{static_folder}/js', 'index.js')

            self.create_sub_folder(static_folder, 'scss')
            self.create_file(f'{static_folder}/scss', 'styles.scss')

            self.create_sub_folder(static_folder, 'images')

    def create_sub_folder(self, static_folder, folder):
        folder_path = os.path.join(static_folder, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def create_file(self, folder, filename):
        open(f'{folder}/{filename}', 'w')





