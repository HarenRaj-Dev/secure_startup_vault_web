from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'png', 'jpg', 'jpeg'}


class UploadFileForm(FlaskForm):
    file = FileField('Select File', validators=[FileRequired(), FileAllowed(ALLOWED_EXTENSIONS, 'Only PDF, TXT, DOCX, PNG, JPG files allowed')])
    submit = SubmitField('Secure to Vault')