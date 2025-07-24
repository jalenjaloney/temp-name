from flask_wtf import FlaskForm
from wtforms import (
    TextAreaField,
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    ValidationError,
)
from wtforms.validators import DataRequired, Regexp, Length, EqualTo
from app.models import User


class RegistrationForm(FlaskForm):
    # username validataion fields
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=2, max=20),
            Regexp(r"^[A-Za-z0-9_.]+$", message="Letters, numbers, ., and _ only."),
        ],
    )

    # password validataion fields
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8),
            Regexp(
                # must contain at least one upper, lower, digit, and special character
                r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$",
                message="Use letters, numbers, and special characters.",
            ),
        ],
    )

    # double check password validataion fields
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )

    # submit validataion fields(?)
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        # Check if username already exists
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username is already taken. Please choose another.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class commentForm(FlaskForm):
    content = TextAreaField("Comment", validators=[DataRequired()])
    timestamp = StringField(
        "Timestamp (HH:MM:SS)",
        validators=[
            DataRequired(),
            Regexp(
                r"^(\d{1,2}:)?[0-5]?\d:[0-5]\d$",
                message="Use HH:MM:SS or MM:SS format"),
        ],
    )
    submit = SubmitField("Post Comment")
