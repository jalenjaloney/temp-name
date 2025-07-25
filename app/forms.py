from flask_wtf import FlaskForm
from wtforms import (
    TextAreaField,
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    ValidationError,
    HiddenField
)
from wtforms.validators import DataRequired, Regexp, Length, EqualTo
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        # Check if username already exists
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "Username is already taken. Please choose another.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class commentForm(FlaskForm):
    content = TextAreaField("Comment")
    timestamp = StringField(
        "Timestamp (HH:MM:SS)",
        validators=[
            DataRequired(),
            Regexp(
                r"^(\d{1,2}:)?[0-5]?\d:[0-5]\d$",
                message="Use HH:MM:SS or MM:SS format"),
        ],
    )
    gif_url = HiddenField("GIF URL")
    submit = SubmitField("Post Comment")

    # Overriding validation logic for entire comment form
    def validate(self, extra_validators=None):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        # Require either text or gif in comment
        has_text = self.content.data and self.content.data.strip()
        has_gif = self.gif_url.data and self.gif_url.data.strip()

        if not has_text and not has_gif:
            self.content.errors.append("Cannot post an empty comment.")
            return False

        return True
